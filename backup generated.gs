function doGet(e) {
  const link = e.parameter.link;
  const extra = e.parameter.extra;

  if (link && extra) {
    const sheet = SpreadsheetApp.openById('1ho1PWZiTgjro2xWE4yWKz1I7ey2vfwr-6wKpb3rs918').getSheetByName('Sheet1');
    const lastRow = sheet.getLastRow();
    const newRow = lastRow + 1;

    sheet.getRange(newRow, 1).setValue('DAGET');
    sheet.getRange(newRow, 2).setValue("Dana kaget LINK "+ newRow);
    sheet.getRange(newRow, 3).setValue(`https://muraproject.github.io/muraplayer/generate.html?extra=${extra}`);
    sheet.getRange(newRow, 4).setValue('https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSqhPf3E4Y_8vAyNJIjkvvW_q_Yeo9FQOdX6Vr3VK1JXNCtGkrIsLyVO00&s=10');
    sheet.getRange(newRow, 5).setValue('gaskan makin banyak hati hati ada yang kosong');

    return ContentService.createTextOutput(extra);
  } else if(extra){
    const sheet = SpreadsheetApp.openById('1ho1PWZiTgjro2xWE4yWKz1I7ey2vfwr-6wKpb3rs918').getSheetByName('Sheet1');
    const lastRow = sheet.getLastRow();
    const newRow = lastRow + 1;

    sheet.getRange(newRow, 1).setValue('DAGET');
    sheet.getRange(newRow, 2).setValue("Dana kaget LINK "+ newRow);
    sheet.getRange(newRow, 3).setValue(`https://muchamatrifaiali.github.io/file-project/res/kosong.html?kode=${extra}`);
    sheet.getRange(newRow, 4).setValue('https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSqhPf3E4Y_8vAyNJIjkvvW_q_Yeo9FQOdX6Vr3VK1JXNCtGkrIsLyVO00&s=10');
    sheet.getRange(newRow, 5).setValue('gaskan makin banyak hati hati ada yang kosong');
    return ContentService.createTextOutput('kosong disimpan');
  }
    else {
    return ContentService.createTextOutput('Link atau extra parameter tidak valid.');
  }
}
