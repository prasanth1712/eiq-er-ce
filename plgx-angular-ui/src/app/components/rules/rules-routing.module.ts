import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { IocComponent } from './ioc/ioc.component';
import { YaraComponent } from './yara/yara.component';
import { RuleComponent } from './rule/rule.component';
import { AddRuleComponent } from './rule/add-rule/add-rule.component';
import { EditRuleComponent } from './rule/edit-rule/edit-rule.component';
 import { AlertsComponent } from 'src/app/widgets/alerts/alerts.component';

const routes: Routes = [
  {
      path: '',
      children: [
          {
            path: 'er-rules',
            children: [
              {path: '', component: RuleComponent},
              {path: 'add-rule', component: AddRuleComponent},
              {path: ':id/edit', component: EditRuleComponent},
            ]
          },
          {
              path: 'ioc-rules',
              component: IocComponent
          },
          {
              path: 'yara',
              component: YaraComponent
          },
          {
            path: ':id/edit',
            redirectTo: 'er-rules/:id/edit'
          },
        ]
    }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class RulesRoutingModule { }
