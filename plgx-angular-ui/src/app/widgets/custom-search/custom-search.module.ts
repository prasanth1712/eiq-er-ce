import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CustomSearchComponent } from '../custom-search/custom-search.component';
import { RouterModule } from '@angular/router';


@NgModule({
  declarations: [CustomSearchComponent],
  imports: [
    CommonModule,
    RouterModule
  ],exports: [
    CustomSearchComponent
  ]
})
export class CustomSearchModule { }