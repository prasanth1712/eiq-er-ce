import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { GlobalModule } from '../../global/global.module';
import { NgJsonEditorModule } from 'ang-jsoneditor';
import { ConfigComponent } from './config/config.component';
import { PacksComponent } from './packs/packs.component';
import { QueriesComponent } from './queries/queries.component';
import { UpdateQueryInPacksComponent } from './packs/update-query-in-packs/update-query-in-packs.component';
import { AddQueryComponent } from './queries/add-query/add-query.component';
import { UpdateQueriesInQueriesComponent } from './queries/update-queries-in-queries/update-queries-in-queries.component';
import { TagComponent } from './tag/tag.component';
import { TaggedComponent } from './tag/tagged/tagged.component';
import { AngularMultiSelectModule } from 'angular2-multiselect-dropdown';
import { HostsConfigurationRoutingModule } from './hosts-configuration-routing.module';
import { HostsConfigurationComponent } from './hosts-configuration.component';
import { AceEditorModule } from "ng2-ace-editor";
import { TagInputModule } from 'ngx-chips';
import { DataTablesModule } from 'angular-datatables';
import { Ng2SearchPipeModule } from 'ng2-search-filter';
import { SharedModule } from 'src/app/shared/shared.module';
import { HttpClientModule,HTTP_INTERCEPTORS } from '@angular/common/http';
import { AuthInterceptor } from 'src/app/_helpers/auth.interceptor';
@NgModule({
  declarations: [HostsConfigurationComponent,ConfigComponent,PacksComponent,QueriesComponent,UpdateQueryInPacksComponent,AddQueryComponent,UpdateQueriesInQueriesComponent,TagComponent,TaggedComponent],
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    ReactiveFormsModule,
    GlobalModule,
    NgJsonEditorModule,
    AngularMultiSelectModule,
    HostsConfigurationRoutingModule,
    AngularMultiSelectModule,
    AceEditorModule,
    TagInputModule,
    DataTablesModule,
    Ng2SearchPipeModule,
    SharedModule
  ],
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true }
  ],
})
export class HostsConfigurationModule { }
