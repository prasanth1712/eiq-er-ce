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
import {DatepickerModule} from "ng2-datepicker";
import {NgbDatepickerModule, NgbModule} from '@ng-bootstrap/ng-bootstrap';
import { SharedModule } from "../../shared/shared.module";
import { AngularMultiSelectModule } from 'angular2-multiselect-dropdown';
import { NgMultiSelectDropDownModule } from 'ng-multiselect-dropdown';
import { NgSelectModule } from '@ng-select/ng-select';
import { HostsModule } from 'src/app/components/hosts/hosts.module';
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
    DatepickerModule,
    NgbDatepickerModule,
    SharedModule,
    NgbModule,
    AngularMultiSelectModule,
    NgMultiSelectDropDownModule,
    NgSelectModule,
    HostsModule
    // TableModule,
  ],
  exports:[AlertsComponent]
})
export class AlertsModule { }
