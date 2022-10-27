import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ReactiveFormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';

import { DashbordRoutingModule } from './dashbord-routing.module';
import { DashboardComponent } from './dashboard.component';
import { AdminAsideComponent } from '../layout/admin-aside/admin-aside.component';
// import { AdminContentComponent } from '/admin-content/admin-content.component';
import { CarvesComponent } from '../components/carves/carves.component';
import { HostsComponent } from '../components/hosts/hosts.component';
import { HuntComponent } from '../components/hunt/hunt.component';
import { LiveQueriesComponent } from '../components/live-queries/live-queries.component';
import { SearchComponent } from '../components/search/search.component';
import { QueryBuilderModule } from "angular2-query-builder";
import { NodesComponent } from '../components/hosts/nodes/nodes.component';
import { ActivityComponent } from '../components/hosts/activity/activity.component';
// import { QueryUpdateComponent } from '../components/query-update/query-update.component';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
// import {TableModule} from 'primeng/table';
import { TagInputModule } from 'ngx-chips';
import { DataTablesModule } from 'angular-datatables';
import { Ng2SearchPipeModule } from 'ng2-search-filter';
import { DateAgoPipe } from './pipes/date-ago.pipe';
// import { NodeFilterComponent } from './node-filter/node-filter.component';
import {NgxPaginationModule} from 'ngx-pagination';
import { NgJsonEditorModule } from 'ang-jsoneditor';
import { ShortNumberPipe } from './pipes/short-number.pipe';
import { LogoutComponent } from '../logout/logout.component';
import { GlobalModule } from '../global/global.module';
import { SharedModule } from '../shared/shared.module';
// import { Timeline } from 'vis-timeline';
@NgModule({
  declarations: [
    DashboardComponent,
    // AdminAsideComponent,
    // AdminContentComponent,
    // AlertsComponent,
    // CarvesComponent,
    // ConfigComponent,
    // HostsComponent,
    // HuntComponent,
    // IocComponent,
    // LiveQueriesComponent,
    // LogoutComponent,
    // OptionsComponent,
    // PacksComponent,
    // QueriesComponent,
    // RuleComponent,
    // SearchComponent,
    // TagComponent,
    // YaraComponent,
    // ServicesComponent,
    // AlienvaultComponent,
    // IbmxforceComponent,
    // RuleAlertsComponent,
    // VirusTotalAlertsComponent,
    // NodesComponent,
    // ActivityComponent,
    // QueryComponent,
    // QueryUpdateComponent,
    ///DateAgoPipe,
    // NodeFilterComponent,
    // AlertDataComponent,

    // Openc2Component,
    // AddOpenc2Component,
    // AddRuleComponent,
    // EditRuleComponent,
    // UpdateQueryInPacksComponent,
    // AddQueryComponent,
    // UpdateQueriesInQueriesComponent,
    // TaggedComponent,
    ShortNumberPipe,
   // TestComponent,
  ],
  imports: [
    CommonModule,
    DashbordRoutingModule,
    FormsModule,
    ReactiveFormsModule,
    QueryBuilderModule,
    HttpClientModule,
    DataTablesModule,
    // BrowserAnimationsModule,
    // TableModule,
    TagInputModule,
    Ng2SearchPipeModule,
    NgJsonEditorModule,
    NgxPaginationModule,
    GlobalModule,
    SharedModule
  ]
})
export class DashboardModule { }
