// Generates a temporary link with extra data



function generateTempLink(extraData) {
  const code = Math.random().toString(36).substring(2, 15);
  const expiration = Date.now() + 60000; // 1 minute from now

  // Get the active spreadsheet and Sheet1
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Sheet1');
  sheet.appendRow([code, expiration, false, extraData]);
  generateCount();
  
  const url = "https://muraproject.github.io/muraplayer/klaim.html?code=" + code;
  return url;
}

// Main function to handle GET requests
function doGet(e) {
  
  
  const action = e.parameter.action;

  const code = e.parameter.code;
  const extraData = e.parameter.extraData; // Additional data passed as parameter

  if (action === 'generate') {
    const url = generateTempLink(extraData);
    return ContentService.createTextOutput(url);
  }
  if (action === 'danaku') {

    return renderCeking("data");

  }
  

  if (code) {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Sheet1');
    const data = sheet.getDataRange().getValues();
    
    for (let i = 1; i < data.length; i++) { // Skip the header row
      if (data[i][0] === code) {
        const expiration = data[i][1];
        const accessed = data[i][2];
        const storedExtraData = data[i][3];
        
        // Check if the link is expired or already accessed
        if (Date.now() > expiration) {
          sheet.deleteRow(i + 1); // Clean up expired link (adjust for header)
          return ContentService.createTextOutput("invalid link").setMimeType(ContentService.MimeType.TEXT);
        }
        
        if (accessed) {
          return ContentService.createTextOutput("link sudah di klaim").setMimeType(ContentService.MimeType.TEXT);
        }
        
        // Mark link as accessed
        sheet.getRange(i + 1, 3).setValue(true); // Update 'Accessed' column
        
        // Serve the content or redirect as necessary
        claimCount();
        return redirect("link sesuai intent://link.dana.id/kaget?c=" + storedExtraData+"#Intent;package=id.dana;scheme=https;end");
        
      }
    }
  }

  return ContentService.createTextOutput("invalid link").setMimeType(ContentService.MimeType.TEXT);
}

// Function to clear expired links (run this periodically, e.g., daily)
function clearExpiredLinks() {
  // Mengakses lembar kerja bernama 'Sheet1'
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Sheet1');
  
  // Mendapatkan semua data di lembar kerja
  const data = sheet.getDataRange().getValues();
  
  // Mendapatkan waktu saat ini dalam milidetik
  const now = Date.now();
  
  // Menambahkan 5 menit (300000 milidetik) ke waktu saat ini
  const expirationTime = now + 5 * 60 * 1000;
  
  // Melakukan iterasi mundur dari baris terakhir ke baris pertama untuk menghindari masalah indeks saat menghapus baris
  for (let i = data.length - 1; i > 0; i--) {
    // Jika nilai di kolom kedua (B) kurang dari waktu saat ini ditambah 5 menit
    if (data[i][1] < expirationTime) {
      // Menghapus baris. Indeks di `deleteRow` harus ditambah 1 karena indeks baris mulai dari 1, bukan 0
      sheet.deleteRow(i + 1);
    }
  }
}


// Function to render HTML with a status message
function renderHtml(statusMessage) {
  const template = HtmlService.createTemplateFromFile('response');
  template.statusMessage = statusMessage;
  return template.evaluate().setSandboxMode(HtmlService.SandboxMode.IFRAME);
}

function renderCeking(statusMessage) {
  const template = HtmlService.createTemplateFromFile('redir');
  template.statusMessage = statusMessage;
  return template.evaluate().setSandboxMode(HtmlService.SandboxMode.IFRAME);
}

function redirect(statusMessage) {
  const template = HtmlService.createTemplateFromFile('redirect');
  
  template.statusMessage = statusMessage;
  Logger.log(template.getRawContent());
  
  // return template.evaluate().setSandboxMode(HtmlService.SandboxMode.NATIVE);
   return ContentService.createTextOutput(statusMessage).setMimeType(ContentService.MimeType.TEXT);
  // return HtmlService.createHtmlOutput('<b>Hello, world!</b>');
}
function generateCount(){
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Sheet1');
  const data = sheet.getRange('F1').getValue();
  sheet.getRange('F1').setValue(data+1);
  Logger.log(data);
}

function claimCount(){
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Sheet1');
  const data = sheet.getRange('G1').getValue();
  sheet.getRange('G1').setValue(data+1);
  Logger.log(data);
}
