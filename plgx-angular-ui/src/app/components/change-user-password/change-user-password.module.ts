import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChangeUserPasswordComponent } from './change-user-password.component';
import { ReactiveFormsModule } from '@angular/forms';
import { SharedModule } from "../../shared/shared.module";

@NgModule({
  declarations: [ChangeUserPasswordComponent],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    SharedModule
  ],
  exports:[ChangeUserPasswordComponent]
})
export class ChangeUserPasswordModule { }
