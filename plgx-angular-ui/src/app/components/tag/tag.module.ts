import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { TagRoutingModule } from './tag-routing.module';
import { TagComponent } from './tag.component';
import { GlobalModule } from '../../global/global.module';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { NgJsonEditorModule } from 'ang-jsoneditor';
import { TagInputModule } from 'ngx-chips';
import { Ng2SearchPipeModule } from 'ng2-search-filter';
import { DataTablesModule } from 'angular-datatables';
import { RouterModule } from '@angular/router';
// import { TableModule } from 'primeng/table';
import { TaggedComponent } from './tagged/tagged.component';
import { HttpClientModule } from '@angular/common/http';
import {NgxPaginationModule} from 'ngx-pagination';
import { AngularMultiSelectModule } from 'angular2-multiselect-dropdown';

@NgModule({
  declarations: [TagComponent,TaggedComponent],
  imports: [
    CommonModule,
    TagRoutingModule,
    GlobalModule,
    FormsModule,
    ReactiveFormsModule,
    NgJsonEditorModule,
    TagInputModule,
    Ng2SearchPipeModule,
    DataTablesModule,
    RouterModule,
    // TableModule,
    HttpClientModule,
    NgxPaginationModule,
    AngularMultiSelectModule,

  ]
})
export class TagModule { }
