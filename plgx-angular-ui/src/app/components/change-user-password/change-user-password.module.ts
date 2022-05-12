import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChangeUserPasswordComponent } from './change-user-password.component';
import { ReactiveFormsModule } from '@angular/forms';

@NgModule({
  declarations: [ChangeUserPasswordComponent],
  imports: [
    CommonModule,
    ReactiveFormsModule
  ],
  exports:[ChangeUserPasswordComponent]
})
export class ChangeUserPasswordModule { }
