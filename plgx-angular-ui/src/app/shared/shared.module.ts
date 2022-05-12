import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DateTimeFormatPipe } from '../dashboard/pipes/datetimeformat.pipe';


@NgModule({
  declarations: [DateTimeFormatPipe],
  imports: [
    CommonModule,
  ],exports: [
    DateTimeFormatPipe
  ]
})
export class SharedModule { }
