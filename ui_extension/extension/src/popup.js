import { onPhishStatusAsync } from './utils.js';

/**
 * @param {Element|string} elementOrId
 * @param {string} text
 * @returns {void}
 */
function setElementText(elementOrId, text) {
	const element = typeof elementOrId === 'string'
		? document.getElementById(elementOrId)
		: elementOrId;
	element.textContent = text;
}

/**
 * 
 * @param {Element} element
 * @param {(s: string) => boolean} predicate
 * @returns {void}
 */
function classRemoveBy(element, predicate) {
	const classList = element.classList;

	/** @type string[] */
	const candidates = [];
	classList.forEach((classToken) => {
		if (predicate(classToken)) {
			candidates.push(classToken);
		}
	});
	candidates.forEach(c => classList.remove(c));
}

/**
 * @param {HTMLElement} element
 * @param {string} prefix
 * @param {string} newClass
 */
function toggleTwClass(element, prefix, newClass) {
	classRemoveBy(element, s => s.startsWith(prefix));
	element.classList.add(newClass);
}

document.addEventListener('DOMContentLoaded', function () {
	chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
		const currentTab = tabs[0];
		const url = new URL(currentTab.url);
		const domain = url.hostname;

		chrome.runtime.sendMessage({ action: 'getCheckResult', domain: domain }, (response) => {
			setElementText('base-url', domain);
			setElementText('full-url', url.toString());

			const warningElement = document.getElementById('warning');
			const statusElement = document.getElementById('status');
			const popupHeader = document.getElementById('popup-header');

			if (url.protocol === 'chrome:' || url.protocol === 'chrome-extension:') {
				statusElement.textContent = 'This is a special page, please try visiting a different page.';
				return
			}

			onPhishStatusAsync(response.phish, {
				onPhishing: async () => {
					setElementText(statusElement, 'Phishing');
					setElementText(warningElement, '');
					warningElement.className = '';

					toggleTwClass(popupHeader, 'bg-', 'bg-red-500');
				},
				onSafe: async () => {
					setElementText(statusElement, 'Safe');
					setElementText(warningElement, '');
					warningElement.className = '';

					toggleTwClass(popupHeader, 'bg-', 'bg-blue-700');
				},
				onDefault: async () => {
					setElementText(statusElement, 'Not checked');
					setElementText(warningElement, '');
					warningElement.className = '';

					toggleTwClass(popupHeader, 'bg-', 'bg-blue-700');
				},
			});
		});
	});
});
