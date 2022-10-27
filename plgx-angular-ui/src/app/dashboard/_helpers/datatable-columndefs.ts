import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';


@Injectable({
  providedIn: 'root'
})
export class Datatablecolumndefs {
  constructor() { }

  columnDefs(keys) {
    var columns = [];
    var counter = 0;

    var column_postition_md5;
    var column_postition_sha1;
    var column_postition_domain_name;
    var column_postition_url;

    var md5Exist = false;
    var urlExist = false;
    var domainnameExist = false;
    var sha1Exist = false;

    keys.forEach(function (key) {
       if(key == 'md5') {
         md5Exist = true;
         column_postition_md5 = counter;
       }
       else if(key == 'url'){
         urlExist = true;
         column_postition_url = counter;
       }
       else if(key == 'domain_name'){
         domainnameExist = true;
         column_postition_domain_name = counter;
       }
       else if(key == 'sha1'){
         sha1Exist = true;
         column_postition_sha1 = counter;
       }

      counter++;
      columns.push({data: key, title: key});
    });


    var column_defs = [];
    if (md5Exist) {
      column_defs.push({
        render: function (data, type, full, meta) {
          if (type === 'display') {
            return '<div class="text-wrap width">' + '<a target="_blank" style="color:blue" href="https://www.virustotal.com/#/file/' + data + '/detection' + '" ;>' + data + "</a></div>";
          }
        },
        targets: column_postition_md5,
        sortable: false
      });
    }


    if (urlExist) {
      column_defs.push({
        render: function (data, type, full, meta) {
          if (type === 'display') {
            // return '<div class="text-wrap width">' + '<a target="_blank" href="http://' + data + '" style="color:blue"  >' + data + "</a>" + "</div>";
            return '<div class="text-wrap width">' + '<a target="_blank" href="https://www.virustotal.com/gui/domain/' + data + '/detection" style="color:blue"  >' + data + "</a>" + "</div>"
          }
        }, targets: column_postition_url
      })
    }


    if (domainnameExist) {
      column_defs.push({
        render: function (data, type, full, meta) {
          if (type === 'display' && typeof data != "undefined" ) {
            return '<div class="text-wrap width">' + '<a target="_blank" style="color:blue" href="https://www.virustotal.com/#/domain/' + data.substring(1, data.length) + '" ;>' + data + "</a></div>";
          }
        },
        targets: column_postition_domain_name
      });
    }


    if (sha1Exist) {
      column_defs.push({
        render: function (data, type, full, meta) {
          if (type === 'display') {
            return '<div class="text-wrap width">' + '<a target="_blank" style="color:blue" href="https://www.virustotal.com/#/file/' + data + '/detection' + '" ;>' + data + "</a></div>";
          }
        },
        targets: column_postition_sha1
      });
    }

  var result ={"column":columns,"column_defs":column_defs}
  return result;
  }

}
