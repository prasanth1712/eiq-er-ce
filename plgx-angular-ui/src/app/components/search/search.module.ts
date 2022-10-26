import {NgbDatepickerModule} from '@ng-bootstrap/ng-bootstrap';import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { SearchRoutingModule } from './search-routing.module';
import { SearchComponent } from './search.component';
import { GlobalModule } from '../../global/global.module';
import { QueryBuilderModule } from "angular2-query-builder";
import { DataTablesModule } from 'angular-datatables';
import { DatepickerModule } from 'ng2-datepicker';
import { SharedModule } from 'src/app/shared/shared.module';
import { HttpClientModule,HTTP_INTERCEPTORS } from '@angular/common/http';
import { AuthInterceptor } from 'src/app/_helpers/auth.interceptor';
@NgModule({
  declarations: [SearchComponent],
  imports: [
    CommonModule,
    SearchRoutingModule,
    GlobalModule,
    QueryBuilderModule,
    DataTablesModule,
    DatepickerModule,
    NgbDatepickerModule,
    SharedModule
  ],
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true }
  ],
})
export class SearchModule { }
