import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgJsonEditorModule } from 'ang-jsoneditor';
import { RulesRoutingModule } from './rules-routing.module';
import { GlobalModule } from '../../global/global.module';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { IocComponent } from './ioc/ioc.component';
import { YaraComponent } from './yara/yara.component';
import { RuleComponent } from './rule/rule.component';
import { AddRuleComponent } from './rule/add-rule/add-rule.component';
import { EditRuleComponent } from './rule/edit-rule/edit-rule.component';
// import { AlertsUnderRuleComponent } from './rule/alerts-under-rule/alerts-under-rule.component';
import { QueryBuilderModule } from "angular2-query-builder";
import { RuleSearchPipe } from './rule/rulesearch.pipe';
import { AngularMultiSelectModule } from 'angular2-multiselect-dropdown';
import { DataTablesModule } from 'angular-datatables';
import { SharedModule } from 'src/app/shared/shared.module';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { HttpClientModule,HTTP_INTERCEPTORS } from '@angular/common/http';
import { AuthInterceptor } from 'src/app/_helpers/auth.interceptor';
@NgModule({
  declarations: [IocComponent,YaraComponent,RuleComponent,AddRuleComponent,EditRuleComponent,RuleSearchPipe],
  imports: [
    CommonModule,
    RulesRoutingModule,
    GlobalModule,
    NgJsonEditorModule,
    FormsModule,
    ReactiveFormsModule,
    QueryBuilderModule,
    AngularMultiSelectModule,
    DataTablesModule,
    SharedModule,
    NgbModule
  ],
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true }
  ],
})
export class RulesModule { }
