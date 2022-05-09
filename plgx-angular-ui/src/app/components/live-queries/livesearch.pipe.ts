import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'livesearch'
})

export class LiveSearchPipe implements PipeTransform {  
  transform(records: {}, searchText?: string): any {
    if (!searchText || searchText == "") return records;
    let LiveQueryData={}
    for(const i in records){
       var HostName=String(records[i].hostname.toLowerCase()).includes(searchText.toLowerCase())
       if(HostName){
        LiveQueryData[i]=records[i]
       }
    }
      if(Object.keys(LiveQueryData).length === 0) {
        return [-1];
      }
      else{      
      return LiveQueryData;
      }
      
  }

}