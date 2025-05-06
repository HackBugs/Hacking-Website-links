
# How to Use This Tool
## Install as a userscript:

- **Install Tampermonkey (Chrome) or Greasemonkey (Firefox)**

- **Create a new script and paste this entire code**

- **Save and refresh your video page**

# Advanced Video URL Grabber Tool
Powerful browser-based tool that mimics IDM's detection capabilities as closely as possible using JavaScript. This tool actively monitors all network traffic and DOM changes to detect media streams.


```
// ==UserScript==
// @name         Advanced Video Grabber
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Detects video streams like IDM does
// @author       YourName
// @match        *://*/*
// @grant        unsafeWindow
// @grant        GM_setClipboard
// @run-at       document-start
// ==/UserScript==

(function() {
    'use strict';

    // Configuration
    const MEDIA_TYPES = [
        'video/mp4', 'video/webm', 'video/ogg', 'video/avi', 'video/x-msvideo',
        'video/x-matroska', 'video/quicktime', 'video/x-flv', 'application/x-mpegURL'
    ];
    
    const MEDIA_EXTS = [
        'mp4', 'webm', 'ogg', 'avi', 'mkv', 'mov', 'flv', 'm3u8', 'ts',
        'mp3', 'aac', 'wav', 'm4a', 'm4v', 'f4v', '3gp'
    ];
    
    // Detection engine
    class VideoDetector {
        constructor() {
            this.mediaUrls = new Set();
            this.init();
        }
        
        init() {
            this.hookNetworkRequests();
            this.monitorDOMChanges();
            this.scanExistingMedia();
            this.setupUI();
        }
        
        hookNetworkRequests() {
            // Hook XMLHttpRequest
            const originalXHR = window.XMLHttpRequest;
            window.XMLHttpRequest = function() {
                const xhr = new originalXHR();
                const originalOpen = xhr.open;
                xhr.open = (method, url) => {
                    this.checkUrl(url);
                    return originalOpen.apply(xhr, arguments);
                };
                return xhr;
            };
            
            // Hook fetch API
            const originalFetch = window.fetch;
            window.fetch = (...args) => {
                const url = args[0] instanceof Request ? args[0].url : args[0];
                this.checkUrl(url);
                return originalFetch(...args);
            };
            
            // Monitor performance entries
            setInterval(() => {
                performance.getEntriesByType('resource').forEach(entry => {
                    this.checkUrl(entry.name);
                });
            }, 2000);
        }
        
        monitorDOMChanges() {
            const observer = new MutationObserver(mutations => {
                mutations.forEach(mutation => {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === 1) { // Element node
                            this.checkMediaElement(node);
                            if (node.querySelectorAll) {
                                node.querySelectorAll('video, audio, source, embed, iframe').forEach(el => {
                                    this.checkMediaElement(el);
                                });
                            }
                        }
                    });
                });
            });
            
            observer.observe(document, {
                childList: true,
                subtree: true
            });
        }
        
        scanExistingMedia() {
            document.querySelectorAll('video, audio, source, embed, iframe').forEach(el => {
                this.checkMediaElement(el);
            });
            
            // Scan scripts for media URLs
            document.querySelectorAll('script').forEach(script => {
                const content = script.textContent;
                MEDIA_EXTS.forEach(ext => {
                    const regex = new RegExp(`https?://[^"']+?\\.${ext}(?:[^"']*)?`, 'gi');
                    const matches = content.match(regex);
                    if (matches) {
                        matches.forEach(url => this.mediaUrls.add(url));
                    }
                });
            });
        }
        
        checkMediaElement(el) {
            const sources = [];
            
            if (el.src) sources.push(el.src);
            if (el.currentSrc) sources.push(el.currentSrc);
            if (el.data) sources.push(el.data);
            
            if (el.tagName === 'VIDEO' || el.tagName === 'AUDIO') {
                el.querySelectorAll('source').forEach(source => {
                    if (source.src) sources.push(source.src);
                });
            }
            
            sources.forEach(url => this.checkUrl(url));
        }
        
        checkUrl(url) {
            if (!url) return;
            
            // Check by extension
            const extMatch = url.match(/\.([a-z0-9]+)(?:[?#]|$)/i);
            if (extMatch && MEDIA_EXTS.includes(extMatch[1].toLowerCase())) {
                this.addMediaUrl(url);
                return;
            }
            
            // Check by content type patterns
            if (url.includes('videoplayback') || 
                url.includes('manifest') || 
                url.includes('segment') || 
                url.includes('/video/') || 
                url.includes('/stream/')) {
                this.addMediaUrl(url);
                return;
            }
        }
        
        addMediaUrl(url) {
            if (!this.mediaUrls.has(url)) {
                this.mediaUrls.add(url);
                this.updateUI();
                console.log('[Video Grabber] Detected media URL:', url);
                
                // Try to copy to clipboard
                try {
                    GM_setClipboard(url, 'text');
                } catch (e) {
                    navigator.clipboard.writeText(url).catch(() => {});
                }
            }
        }
        
        setupUI() {
            // Create UI elements
            const style = document.createElement('style');
            style.textContent = `
                .video-grabber-panel {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    z-index: 999999;
                    background: white;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    padding: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                    max-width: 400px;
                    max-height: 300px;
                    overflow: auto;
                }
                .video-grabber-title {
                    font-weight: bold;
                    margin-bottom: 10px;
                }
                .video-grabber-url {
                    word-break: break-all;
                    margin: 5px 0;
                    padding: 5px;
                    border-bottom: 1px solid #eee;
                }
                .video-grabber-copy {
                    background: #4CAF50;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                    cursor: pointer;
                    margin-top: 10px;
                }
            `;
            document.head.appendChild(style);
            
            const panel = document.createElement('div');
            panel.className = 'video-grabber-panel';
            panel.innerHTML = `
                <div class="video-grabber-title">Detected Media URLs</div>
                <div id="video-grabber-urls"></div>
                <button class="video-grabber-copy" id="video-grabber-copy-all">Copy All URLs</button>
            `;
            document.body.appendChild(panel);
            
            // Add copy button handler
            document.getElementById('video-grabber-copy-all').addEventListener('click', () => {
                const urls = Array.from(this.mediaUrls).join('\n');
                try {
                    GM_setClipboard(urls, 'text');
                } catch (e) {
                    navigator.clipboard.writeText(urls).then(() => {
                        alert('All URLs copied to clipboard!');
                    }).catch(() => {
                        prompt('Copy these URLs:', urls);
                    });
                }
            });
            
            this.uiPanel = panel;
            this.uiUrls = document.getElementById('video-grabber-urls');
        }
        
        updateUI() {
            if (!this.uiUrls) return;
            
            this.uiUrls.innerHTML = '';
            Array.from(this.mediaUrls).forEach(url => {
                const urlEl = document.createElement('div');
                urlEl.className = 'video-grabber-url';
                urlEl.textContent = url;
                this.uiUrls.appendChild(urlEl);
            });
        }
    }

    // Start the detector
    new VideoDetector();
})();
```
