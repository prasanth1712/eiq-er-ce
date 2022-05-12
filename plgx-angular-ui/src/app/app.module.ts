import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { GoogleChartsModule } from 'angular-google-charts';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { AuthInterceptor } from './_helpers/auth.interceptor';
// import { ErrorInterceptor } from './_helpers/error.interceptor';
import { GlobalComponent } from './global/global.component';
import { LayoutModule } from './layout/layout.module';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { CommonModule } from '@angular/common';
import { LogoutComponent } from './logout/logout.component';
import { ToastrModule } from 'ngx-toastr';
import { PagenotfoundComponent } from './components/pagenotfound/pagenotfound.component';
import {NgxMaterialTimepickerModule} from 'ngx-material-timepicker';
@NgModule({
  declarations: [
    AppComponent,
    GlobalComponent,
    LogoutComponent,
    // PagenotfoundComponent
  ],
  imports: [
    CommonModule,
    BrowserModule,
    BrowserAnimationsModule,
    AppRoutingModule,
    HttpClientModule,
    GoogleChartsModule.forRoot(),
    LayoutModule,
    ToastrModule.forRoot(),
    NgxMaterialTimepickerModule,
   
  ],
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true }
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
