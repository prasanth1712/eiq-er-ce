import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'appbutton',
  templateUrl: './button.component.html',
  styleUrls: ['./button.component.css']
})
export class ButtonComponent implements OnInit {

  @Input() text: string;
  @Input() btnClass: string;
  @Input() btnType: string;
  @Input() icon: string;
  @Input() isLoading = false;
  @Input() isDisabled = false;
  @Input() modalDismiss: string;
  @Input() btnLink: string;
  @Output() OnClick = new EventEmitter();
  constructor() { }

  ngOnInit(): void {
    
  }
  emitEvent(){
    this.OnClick.emit('test');
  }
  
}
