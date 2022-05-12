import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HostsRoutingModule } from './hosts-routing.module';
import { GlobalModule } from '../../global/global.module';
import { HostsComponent } from './hosts.component';
import { NodesComponent } from './nodes/nodes.component';
import { ActivityComponent } from './activity/activity.component';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { TagInputModule } from 'ngx-chips';
import { Ng2SearchPipeModule } from 'ng2-search-filter';
import { DataTablesModule } from 'angular-datatables';
import { QueryBuilderModule } from "angular2-query-builder";

import { RouterModule } from '@angular/router';
// import {TableModule} from 'primeng/table';
import { HttpClientModule } from '@angular/common/http';
import { NgJsonEditorModule } from 'ang-jsoneditor';
import {NgxPaginationModule} from 'ngx-pagination';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { HostSearchPipe } from '../../dashboard/pipes/host-search.pipe';
import { ActivitySearchPipe } from './Activity-search.pipe';
import {NgDatepickerModule} from "ng2-datepicker";
import { FilterAlertsWithHostnameComponent } from './filter-alerts-with-hostname/filter-alerts-with-hostname.component';
import {NgxMaterialTimepickerModule} from 'ngx-material-timepicker';
import { ToastrModule } from 'ngx-toastr';
import { AngularMultiSelectModule } from 'angular2-multiselect-dropdown';
import { AceEditorModule } from 'ng2-ace-editor';
import { SharedModule } from '../../shared/shared.module';
@NgModule({
  declarations: [HostsComponent,NodesComponent,ActivityComponent,HostSearchPipe,ActivitySearchPipe,FilterAlertsWithHostnameComponent],
  imports: [
    CommonModule,
    GlobalModule,
    HostsRoutingModule,
    FormsModule,
    ReactiveFormsModule,
    QueryBuilderModule,
    HttpClientModule,
    DataTablesModule,
    // TableModule,
    TagInputModule,
    Ng2SearchPipeModule,
    NgJsonEditorModule,
    NgxPaginationModule,
    NgDatepickerModule,
    NgxMaterialTimepickerModule,
    ToastrModule.forRoot(),
    AngularMultiSelectModule,
    AceEditorModule,
    SharedModule

  ],
  exports:[HostsComponent,NodesComponent,ActivityComponent],
})
export class HostsModule { }
