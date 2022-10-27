import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { RuleRoutingModule } from './rule-routing.module';
import { RuleComponent } from './rule.component';
import { GlobalModule } from '../../../global/global.module';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { TagInputModule } from 'ngx-chips';
import { Ng2SearchPipeModule } from 'ng2-search-filter';
import { DataTablesModule } from 'angular-datatables';
import { RouterModule } from '@angular/router';
// import {TableModule} from 'primeng/table';
import { AddRuleComponent } from './add-rule/add-rule.component';
import { EditRuleComponent } from './edit-rule/edit-rule.component';
import { QueryBuilderModule } from "angular2-query-builder";
import { RuleSearchPipe } from './rulesearch.pipe';
import { AngularMultiSelectModule } from 'angular2-multiselect-dropdown';
import { NgJsonEditorModule } from 'ang-jsoneditor';
import { SharedModule } from 'src/app/shared/shared.module';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

@NgModule({
  declarations: [RuleComponent, AddRuleComponent,EditRuleComponent,RuleSearchPipe],
  imports: [
    CommonModule,
    RuleRoutingModule,
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    TagInputModule,
    GlobalModule,
    Ng2SearchPipeModule,
    DataTablesModule,
    RouterModule,
    // TableModule,
    QueryBuilderModule,
    AngularMultiSelectModule,
    NgJsonEditorModule,
    SharedModule,
    NgbModule,
  ]
})
export class RuleModule { }
