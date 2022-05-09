import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { AlertsRoutingModule } from './alerts-routing.module';
import { AlertsComponent } from './alerts.component';
import { NgJsonEditorModule } from 'ang-jsoneditor';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { TagInputModule } from 'ngx-chips';
import { Ng2SearchPipeModule } from 'ng2-search-filter';
import { DataTablesModule } from 'angular-datatables';
import { RouterModule } from '@angular/router';
import { GlobalModule } from '../../global/global.module';
import {NgDatepickerModule} from "ng2-datepicker";
import {NgbDatepickerModule} from '@ng-bootstrap/ng-bootstrap';
@NgModule({
  declarations: [AlertsComponent],
  imports: [
    CommonModule,
    AlertsRoutingModule,
    NgJsonEditorModule,
    GlobalModule,
    FormsModule,
    ReactiveFormsModule,
    TagInputModule,
    Ng2SearchPipeModule,
    DataTablesModule,
    RouterModule,
    NgDatepickerModule,
    NgbDatepickerModule
    // TableModule,
  ]
})
export class AlertsModule { }
