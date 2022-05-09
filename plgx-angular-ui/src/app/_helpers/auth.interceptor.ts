import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent } from "@angular/common/http";
import { Observable } from "rxjs";
import { Injectable, Compiler } from "@angular/core";
import { Router } from "@angular/router";
import { tap } from 'rxjs/operators';
import { ToastrService } from 'ngx-toastr';


@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(
    private _router: Router,
    private _compiler: Compiler,
    private toastr: ToastrService,
  ) { }

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    this._compiler.clearCache();
    if (localStorage.getItem('token')) {
      req = req.clone({
        setHeaders: {
          'x-access-token': localStorage.getItem('token'),
        }
      });
    }
    return next.handle(req)
      .pipe(tap(
        succ => {
        },
        err => {
          if (err.status === 401) {
            this.toastr.error('Session Expired');
            setTimeout(()=>{ this.clearData() }, 2000);
          }
          else if (err.status === 403) {
            this.toastr.error('You are not authorized to perform this action');
          }
          else if (err.status === 404) {
            const validationError = err.error;
          }
          else if (err.status === 400) {
            const validationError = err.error;
          }
        }
      ));
  }
  clearData() {
    localStorage.removeItem('reset_password');
    localStorage.removeItem('roles');
    localStorage.removeItem('all_roles');
    localStorage.removeItem('token');
    this._router.navigate(['./authentication/login']);
  }
}
