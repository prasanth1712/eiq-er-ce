import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { PacksRoutingModule } from './packs-routing.module';
import { PacksComponent } from './packs.component';
import { GlobalModule } from '../../global/global.module';
import { FormsModule } from '@angular/forms';
import { ReactiveFormsModule } from '@angular/forms';
import { TagInputModule } from 'ngx-chips';
import { Ng2SearchPipeModule } from 'ng2-search-filter';
import { DataTablesModule } from 'angular-datatables';
import { RouterModule } from '@angular/router';
// import { TableModule } from 'primeng/table';
import { UpdateQueryInPacksComponent } from './update-query-in-packs/update-query-in-packs.component';
import { PackSearchPipe } from './packs-search.pipe';
import { AngularMultiSelectModule } from 'angular2-multiselect-dropdown';
import { AceEditorModule } from "ng2-ace-editor";
import { SharedModule } from 'src/app/shared/shared.module';

@NgModule({
  declarations: [PacksComponent, UpdateQueryInPacksComponent, PackSearchPipe],
  imports: [
    CommonModule,
    PacksRoutingModule,
    GlobalModule,
    FormsModule,
    ReactiveFormsModule,
    TagInputModule,
    Ng2SearchPipeModule,
    DataTablesModule,
    RouterModule,
    // TableModule,
    AngularMultiSelectModule,
    AceEditorModule,
    SharedModule
  ]
})
export class PacksModule { }
