import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CustomSingleSelectComponent } from './custom-single-select.component';
import { NgMultiSelectDropDownModule } from 'ng-multiselect-dropdown';


@NgModule({
  declarations: [CustomSingleSelectComponent],
  imports: [
    CommonModule,
    NgMultiSelectDropDownModule.forRoot()
  ],
  exports: [
    CustomSingleSelectComponent
  ]
})
export class CustomSingleSelectModule { }

