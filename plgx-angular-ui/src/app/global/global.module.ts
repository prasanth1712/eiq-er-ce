import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { DataTablesModule } from 'angular-datatables';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
// import { TableModule } from 'primeng/table';
import { TagInputModule } from 'ngx-chips';
import { Ng2SearchPipeModule } from 'ng2-search-filter';
import { NgJsonEditorModule } from 'ang-jsoneditor';
import { NgxPaginationModule } from 'ngx-pagination';
import { Router, RouterModule } from '@angular/router';
import { DateAgoPipe } from '../dashboard/pipes/date-ago.pipe';
import { SearchPipe } from '../dashboard/pipes/search.pipe';

import { AppHasRoleDirective } from '../dashboard/_services/app-has-role.directive';

@NgModule({
  declarations: [DateAgoPipe,SearchPipe,AppHasRoleDirective],
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    HttpClientModule,
    DataTablesModule,
    // TableModule,
    TagInputModule,
    Ng2SearchPipeModule,
    NgJsonEditorModule,
    NgxPaginationModule,
    RouterModule,

  ],
  exports:[DateAgoPipe,SearchPipe,AppHasRoleDirective]
})
export class GlobalModule { }
