import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'querysearch'
})

export class QuerySearchPipe implements PipeTransform {  
  transform(records: Array<any>, searchText?: string): any { 

    if (!searchText || searchText == "") return records;


    
     var data =  records.filter(
      (val)=> String(val).toLowerCase().includes(searchText.toLowerCase()))

      if(data.length === 0) {
        return [-1];
      }
      else
      {
      return data;
      }
  }

}