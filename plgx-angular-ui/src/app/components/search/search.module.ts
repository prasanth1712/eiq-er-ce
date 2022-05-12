import {NgbDatepickerModule} from '@ng-bootstrap/ng-bootstrap';import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { SearchRoutingModule } from './search-routing.module';
import { SearchComponent } from './search.component';
import { GlobalModule } from '../../global/global.module';
import { QueryBuilderModule } from "angular2-query-builder";
import { DataTablesModule } from 'angular-datatables';
import { NgDatepickerModule } from 'ng2-datepicker';
@NgModule({
  declarations: [SearchComponent],
  imports: [
    CommonModule,
    SearchRoutingModule,
    GlobalModule,
    QueryBuilderModule,
    DataTablesModule,
    NgDatepickerModule,
    NgbDatepickerModule
  ]
})
export class SearchModule { }
