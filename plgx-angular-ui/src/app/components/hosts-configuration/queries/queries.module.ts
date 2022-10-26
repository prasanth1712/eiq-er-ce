import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { QueriesRoutingModule } from './queries-routing.module';
import { QueriesComponent } from './queries.component';
import { GlobalModule } from '../../global/global.module';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { NgJsonEditorModule } from 'ang-jsoneditor';
import { TagInputModule } from 'ngx-chips';
import { Ng2SearchPipeModule } from 'ng2-search-filter';
import { DataTablesModule } from 'angular-datatables';
import { RouterModule } from '@angular/router';
// import { TableModule } from 'primeng/table';
import { AddQueryComponent } from './add-query/add-query.component';
import { UpdateQueriesInQueriesComponent } from './update-queries-in-queries/update-queries-in-queries.component';
import { QuerySearchPipe } from './queries-search.pipe';
import { AngularMultiSelectModule } from 'angular2-multiselect-dropdown';
import { AceEditorModule } from "ng2-ace-editor";
import { SharedModule } from 'src/app/shared/shared.module';

@NgModule({
  declarations: [QueriesComponent,AddQueryComponent,UpdateQueriesInQueriesComponent,QuerySearchPipe],
  imports: [
    CommonModule,
    QueriesRoutingModule,
    NgJsonEditorModule,
    FormsModule,
    ReactiveFormsModule,
    TagInputModule,
    GlobalModule,
    Ng2SearchPipeModule,
    DataTablesModule,
    RouterModule,
    // TableModule,
    AngularMultiSelectModule,
    AceEditorModule,
    SharedModule
  ]
})
export class QueriesModule { }
