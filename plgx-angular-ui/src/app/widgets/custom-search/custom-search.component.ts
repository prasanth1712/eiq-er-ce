import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'search',
  templateUrl: './custom-search.component.html',
  styleUrls: ['./custom-search.component.css']
})
export class CustomSearchComponent implements OnInit {
  classit: any = false;
  

  @Output() OnClick = new EventEmitter();
  @Output() valueChange = new EventEmitter();
  @Input() textInput: any;

  constructor() { }
 

  ngOnInit(): void {  
    
    $('.custom-search').on('keyup', function(){
      var searchValue = (<HTMLInputElement>document.getElementById('customsearch')).value;
      if (searchValue != ''){
        $('.custom-search').addClass("custom-search-typing");
        $('.fa-times').addClass("visible");
      }
       else {
        $('.custom-search').removeClass("custom-search-typing");
        $('.fa-times').removeClass("visible");
      }
    });

  }

  emitEvent(searchTerm){
    this.OnClick.emit('test');
  }


  clearSearch(){
    (<HTMLInputElement>document.getElementById('customsearch')).value = ''
    $('.custom-search').removeClass("custom-search-typing");
    $('.fa-times').removeClass("visible");
  }

  valueChanged() { 
      this.valueChange.emit();
  }
  
}
