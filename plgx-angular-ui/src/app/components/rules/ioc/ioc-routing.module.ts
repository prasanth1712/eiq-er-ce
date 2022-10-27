import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { IocComponent } from './ioc.component';


const routes: Routes = [
  {
    path: '',
    component: IocComponent, 
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class IocRoutingModule { }
