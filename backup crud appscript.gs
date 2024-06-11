function doPost(e) {
  return ceksheet(e);
}

function doGet(e) {
  return ceksheet(e);
}

function ceksheet(e){
  var ss = SpreadsheetApp.getActive();
  var sh = ss.getSheetByName(e.parameter.SH); 
  
  //CREATE
  if (e.parameter.func == "Create") {
    var kode = e.parameter.KODE;
    var nama = e.parameter.NAMA;
    var user = e.parameter.USERNAME;
    var pass = e.parameter.PASSWORD;
    var data=false;
    var lr= sh.getLastRow();
    for(var i=1;i<=lr;i++){
      var data_id = sh.getRange(i, 1).getValue();
      if(data_id==kode){
        data=true;
      } 
    }
    if (data){
      var result= "ID Sudah ada";
    }else{
      var rowData = sh.appendRow([kode,nama,user,pass]);  
      var result="Berhasil Input";
    }
    return ContentService.createTextOutput(result).setMimeType(ContentService.MimeType.TEXT);
  }  
  
    //Read
  if (e.parameter.func == "Read") {
  var kodeFilter = e.parameter.kode; //mengambil nilai parameter kode
  var rg = sh.getDataRange().getValues();
  var data = [];
  var headers = rg[0];

  for (var row = 1; row < rg.length; ++row) {
    //menambahkan filter pada kolom pertama (k1)
    if (rg[row][0] == kodeFilter || !kodeFilter) {
      var obj = {};
      for (var col = 0; col < headers.length; ++col) {
        obj['k'+(col+1)] = rg[row][col];
      }
      data.push(obj);
    }
  }
  data.reverse();
  return ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}


   //Update
    if (e.parameter.func == "Update") {
    var kode = e.parameter.KODE;
    var nama = e.parameter.NAMA;
    var user = e.parameter.USERNAME;
    var pass = e.parameter.PASSWORD;
    var lr= sh.getLastRow();
    for(var i=1;i<=lr;i++){
      var data_id = sh.getRange(i, 1).getValue();
      if(data_id==kode){
       sh.getRange(i, 2).setValue(nama);
       sh.getRange(i, 3).setValue(user);
       sh.getRange(i, 4).setValue(pass);
        return ContentService.createTextOutput("Data berhasil di Update").setMimeType(ContentService.MimeType.TEXT);
        
      } 
    }
     
  }

  function onEdit(e) {
  var sheet = e.source.getActiveSheet();
  var range = e.range;
  var col = range.getColumn();
  var row = range.getRow();
  
  if (col == 3) {
    var url = sheet.getRange(row, col).getValue();
    var data = getMetadata(url);
    sheet.getRange(row, col+1).setValue(data.description);
    sheet.getRange(row, col+2).setValue(data.image);
  }
}

function getMetadata(url) {
  var response = UrlFetchApp.fetch(url);
  var html = response.getContentText();
  var parser = new DOMParser();
  var doc = parser.parseFromString(html, "text/html");
  var metaTags = doc.head.querySelectorAll('meta[property^="og:"]');
  
  var data = {};
  for (var i = 0; i < metaTags.length; i++) {
    var tag = metaTags[i];
    var property = tag.getAttribute("property");
    var content = tag.getAttribute("content");
    data[property.replace("og:", "")] = content;
  }
  
  return data;
}
 

  
   
  
}
