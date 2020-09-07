// ThermoScan Extension 1.0
// Emidio Capriotti - University of Bologna (Italy)


chrome.browserAction.onClicked.addListener(function (activeTab) {

    // Read HTML File
    let code = `document.querySelector('html').innerHTML`;
    var html = chrome.tabs.executeScript(activeTab.id, { code }, function (result) {
                //console.log(result);

		// Call ThermoScan
		function postData(url, data) {
		
		newURL = 'thermoscan.html';
       		chrome.tabs.create({ url: newURL },
			function(tab) {
				var handler = function(tabId, changeInfo) {
				if(tabId === tab.id && changeInfo.status === "complete"){
          				chrome.tabs.onUpdated.removeListener(handler);
          				chrome.tabs.sendMessage(tabId, {url: url, data: data});
        			}
      				}
		      		chrome.tabs.onUpdated.addListener(handler);
      		      		chrome.tabs.sendMessage(tab.id, {url: url, data: data});
			}
		    );
		}
		postData("https://folding.biofold.org/cgi-bin/thermoscan.cgi", {"paper": result});

 	});
});
