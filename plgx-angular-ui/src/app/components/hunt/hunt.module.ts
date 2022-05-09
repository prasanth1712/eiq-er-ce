import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { HuntRoutingModule } from './hunt-routing.module';
import { HuntComponent } from './hunt.component';
import { GlobalModule } from '../../global/global.module';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { DataTablesModule } from 'angular-datatables';
import { AngularMultiSelectModule } from 'angular2-multiselect-dropdown';
import { NgDatepickerModule } from 'ng2-datepicker';
import {NgbDatepickerModule} from '@ng-bootstrap/ng-bootstrap';
@NgModule({
  declarations: [HuntComponent],
  imports: [
    CommonModule,
    HuntRoutingModule,
    GlobalModule,
    FormsModule,
    ReactiveFormsModule,
    DataTablesModule,
    AngularMultiSelectModule,
    NgDatepickerModule,
    NgbDatepickerModule
  ]
})
export class HuntModule { }
