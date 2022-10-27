import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'packsearch'
})

export class PackSearchPipe implements PipeTransform {  
  transform(records: Array<any>, searchText?: string): any { 

    if (!searchText || searchText == "") return records;

     var data =  records.filter(
      (val)=> String(val.toLowerCase()).includes(searchText.toLowerCase()))
      if(data.length === 0) {
        return [-1];
      }
      else
      {
        
      return data;
      }
      
  }

}