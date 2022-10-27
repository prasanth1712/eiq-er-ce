import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { YaraComponent } from './yara.component';


const routes: Routes = [
  {
    path: '',
    component: YaraComponent, 
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class YaraRoutingModule { }
