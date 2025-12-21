import { logGroupEventAsync, logResponse, onPhishStatusAsync } from './utils.js';
import { whitelist } from './whitelist.js';

/** @type {Record<string,string>} */
const urlCheckResults = {};
/** @type {Map<string,boolean>} */
const whitelistMap = new Map();

class PhishResult {
	/**
	 * @param {boolean} isUserWhitelisted
	 * @param {boolean} isGloballyWhitelisted
	 * @param {'safe'|'phishing'} status
	 */
	constructor(isUserWhitelisted, isGloballyWhitelisted, status) {
		this.isUserWhitelisted = isUserWhitelisted;
		this.isGloballyWhitelisted = isGloballyWhitelisted;
		this.status = status;
	}

	get isWhitelisted() {
		return this.isUserWhitelisted || this.isGloballyWhitelisted
	}

	static asUserWhitelisted = new PhishResult(true, false, 'safe')
	static asGloballyWhitelisted = new PhishResult(false, true, 'safe')
	static asSafe = new PhishResult(false, false, 'safe')
	static asPhishing = new PhishResult(false, false, 'phishing')
}

chrome.runtime.onInstalled.addListener(async (_details) => {
	await logGroupEventAsync('event-oninstalled-chrome.storage.local-user-settings', async () => {
		await chrome.storage.local.set({ showBlocklist: false });
	});

	await logGroupEventAsync('event-oninstalled-chrome.storage.local-whitelist', async () => {
		let i = 0;
		for (const whitelistedDomain of whitelist) {
			whitelistMap.set(whitelistedDomain, true);
			chrome.storage.local.set({
				[whitelistedDomain]: PhishResult.asGloballyWhitelisted,
			});
			i++;
		}
		console.log('chrome.storage.local: loaded %i whitelisted domains', i);
		console.log(whitelist);
	});
});

// Listener for checking URLs
chrome.webRequest.onCompleted.addListener(
	async (details) => {
		if (details.type !== 'main_frame') {
			return
		}

		const url = new URL(details.url);
		const domain = url.hostname;
		const tabId = details.tabId;

		if (url.protocol === 'chrome:' || url.protocol === 'chrome-extension:') {
			urlCheckResults[domain] = 'safe';
			return
		}

		if (whitelistMap.has(domain) || Object.hasOwn(urlCheckResults, domain)) {
			await logGroupEventAsync(`event-oncompleted-visited-whitelisted-domain:${domain}`, async () => {
				console.log(url);
			});
			return
		}

		let phishHtmlText = '';
		await logGroupEventAsync('event-oncompleted-fetch-public/phishing.html', async () => {
			try {
				const response = await getPagePhishing();
				phishHtmlText = await response.text();
				logResponse(response);
			}
			catch (e) {
				console.error(e);
			}
		});

		await logGroupEventAsync(`event-oncompleted-freephish-scan:${url}`, async () => {
			try {
				const response = await getFreePhishCheckUrl(url);
				const data = await response.json();
				const nowSeconds = Date.now();
				const nowDate = new Date(nowSeconds);

				console.log({
					timestampRaw: nowSeconds,
					timestampIso: nowDate.toISOString(),
					tabId: tabId,
					site: url,
					httpResponse: response,
					httpResponseJson: data,
				});

				await onPhishResultEvent({
					phishResult: data.result,
					phishHtmlText: phishHtmlText,
					domain: domain,
					url: url.toString(),
					tabId: tabId,
				});
			}
			catch (e) {
				console.error(e);
			}
		});
	},
	{ urls: ['<all_urls>'] },
);

// Listener for handling messages from content scripts or popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
	switch (message.action) {
		case 'closeTab':
			{
				chrome.tabs.remove(message.tabId);
			}
			break
		case 'getCheckResult':
			{
				sendResponse({
					phish: urlCheckResults[message.domain],
				});
			}
			break
		case 'markSafe':
			{
				urlCheckResults[message.domain] = 'safe';
				whitelistMap[message.domain] = true;
				sendResponse({
					phish: urlCheckResults[message.domain],
				});
			}
			break
	}
});

/**
 * @returns {Promise<Response>}
 */
async function getPagePhishing() {
	return await fetch(chrome.runtime.getURL('/public/phishing.html'), {
		method: 'GET',
		headers: {
			Accept: 'text/html',
		},
	})
}

/**
 * @param {URL} url
 * @returns {Promise<Response>}
 */
async function getFreePhishCheckUrl(url) {

	return await fetch('http://localhost:5024/check_url', {

		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify({ url: url.href }),
	})
}

/**
 *
 *
 *
 *
 * @param {Object} context
 * @param {string} context.phishResult
 * @param {string} context.phishHtmlText
 * @param {string} context.domain
 * @param {URL|string} context.url
 * @param {number} context.tabId
 * @returns {Promise<void>}
 */
async function onPhishResultEvent(context) {
	onPhishStatusAsync(context.phishResult, {
		onPhishing: async () => {
			urlCheckResults[context.domain] = 'phishing';
			chrome.storage.local.set({
				[context.domain]: PhishResult.asPhishing,
			});

			await chrome.scripting.executeScript({
				target: { tabId: context.tabId },
				/** @type {(phishHtmlText: string, url: URL, tabId: number) => void} */
				func: (phishHtmlText, url, tabId) => {
					if (phishHtmlText !== '') {
						let oldDocument = document.documentElement.outerHTML;
						document.write(phishHtmlText);

						let styles = document.createElement('link');
						styles.setAttribute('rel', 'stylesheet');
						styles.setAttribute('type', 'text/css');
						styles.setAttribute('href', `chrome-extension://${chrome.runtime.id}/public/dist.css`);
						document.head.appendChild(styles);

						const reportedUrl = document.getElementById('reported-url');
						reportedUrl.textContent = url.toString();

						document.getElementById('close-tab').addEventListener('click', () => {
							chrome.runtime.sendMessage({ action: 'closeTab', tabId: tabId });
						});

						document.getElementById('mark-safe').addEventListener('click', () => {
							chrome.runtime.sendMessage({ action: 'markSafe', tabId: tabId });
							// remove our content, recover old document content
							document.getElementById('freephishing-warning-page').remove();
							document.write(oldDocument);
						});
					}
				},
				args: [
					context.phishHtmlText,
					context.url,
					context.tabId,
				],
			});
		},
		onSafe: async () => {
			urlCheckResults[context.domain] = 'safe';
			chrome.storage.local.set({
				[context.domain]: PhishResult.asSafe,
			});
		},
	});
}
