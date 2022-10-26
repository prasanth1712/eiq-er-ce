import { Component, forwardRef, Output, Input, ViewChild, EventEmitter, OnInit } from '@angular/core';
import { FormControl,FormGroup } from '@angular/forms';
// import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
@Component({
    selector: 'single-select',
    templateUrl: './custom-single-select.component.html',
    styleUrls: ['./custom-single-select.component.css']
})
export class CustomSingleSelectComponent implements OnInit  {
    @Input() public label: string;
    @Input() public options: { value: number; description: string }[];
    @Input() public text: string;
    @Input() public dropdownDivClass: string;
    @Input() public dropdownSelectClass: string;
    @Input() public defaultPlaceholder: string;
    @Input() public selectedIndexInput: any;
    @Output() btnClick = new EventEmitter();
    @Output() valueChange = new EventEmitter<{value}>();


    public ngSelected= [];

    ngFilterSettings ={
      singleSelection: true,
      idField: 'value',
      textField: 'description',
      enableCheckAll: true,
      selectAllText: 'any',
      unSelectAllText: 'Clear All',
      allowSearchFilter: false,
      // limitSelection: -1,
      // clearSearchFilter: true,
      maxHeight: 197,
      itemsShowLimit: 1,
      closeDropDownOnSelection: true,
      showSelectedItemsAtTop: false,
      defaultOpen: false,
      // clearSearchFilter: false
      // closeDropDownOnSelection: true
    }
    selectedIndex: any;
    valueChanged(event: any) {
      console.log('event', event)
      this.selectedIndex = [{
        value: event.value,
        description: event.description
      }]
      // this.selectedIndex = event.value
      this.onChange(event);
      this.valueChange.emit({value: this.selectedIndex[0].value});
      this.onTouched();
    }

    deSelect(){
      this.selectedIndex = undefined
      this.valueChange.emit({value: ' '});
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
    ngOnInit(): void {
        this.defaultPlaceholder = this.defaultPlaceholder ? this.defaultPlaceholder : 'any';
      this.options.forEach(element => {
        if(element.value == this.selectedIndexInput){
          this.ngSelected[0] = element;
        }
      });
    }
}
