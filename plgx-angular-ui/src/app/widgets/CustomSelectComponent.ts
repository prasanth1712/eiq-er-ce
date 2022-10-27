import { Component, forwardRef, Output, Input, ViewChild, EventEmitter } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
@Component({
    selector: 'dropdown',
    template: `
      <div class="select-wrap custom-dropdown dropdown-select col-sm-12 form-control" [ngClass]="dropdownDivClass" style="padding:0px">
        <label class="select-label font-color-grey-elephant" >{{label}}</label>
        <select class="font-color-grey-elephant" [(ngModel)]="selectedIndex" id="" (change)="valueChanged($event.target.value)" [ngClass]="dropdownSelectClass">
          <option *ngFor="let option of options" [disabled]="option.description === 'Select Config'" [value]="option.value">
          {{ option.description }}</option>
        </select>
        <i class="fa fa-caret-down dropdown-arrow" style="pointer-events: none"></i>
      </div>
    `,
    providers: [
      {
        provide: NG_VALUE_ACCESSOR,
        useExisting: forwardRef(() => CustomSelectComponent),
        multi: true
      }
    ]
})
export class CustomSelectComponent implements ControlValueAccessor  {
    @Input() public label: string;
    @Input() public options: { value: number; description: string }[];
    @Input() public text: string;
    @Input() public dropdownDivClass: string;
    @Input() public dropdownSelectClass: string;
    @Output() btnClick = new EventEmitter();
    selectedIndex: number;
    valueChanged(value: any) {
      this.onChange(value);
      this.onTouched();
    }
  
    // CVA implementation
  
    public onChange = (_: any) => {};
    public onTouched = () => {};
  
    // register onChange which we will call when the selected value is changed
    // so that the value is passed back to the form model
    public registerOnChange(fn): void {
      this.onChange = fn;
    }
  
    public registerOnTouched(fn): void {
      this.onTouched = fn;
    }
  
    // sets the selected value based on the corresponding form model value
    public writeValue(value: any): void {
      this.selectedIndex = value;
    }
}
