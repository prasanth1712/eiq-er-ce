import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-datepicker-calendar',
  templateUrl: './datepicker-calendar.component.html',
  styleUrls: ['./datepicker-calendar.component.css']
})
export class DatepickerCalendarComponent implements OnInit {
  model;
  @Input() public label: string;
  constructor() { }

  ngOnInit(): void {
    console.log(this.model)
  }

}
