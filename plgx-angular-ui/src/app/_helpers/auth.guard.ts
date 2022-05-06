import { Injectable } from '@angular/core';
import { Router, CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';


@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {
  constructor(
        private router: Router,
    ) { }
/*
 CanActivate method returns a boolean indicating whether or not navigation to a route should be allowed. If the user isn’t authenticated.then in this case a route called authentication/login
*/

  canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot) {
    if(JSON.parse(localStorage.getItem('reset_password'))){
      this.router.navigate(['./authentication/login'])
    }          
     else if(localStorage.getItem('token')) {
              return true;
    } else {
          this.router.navigate(['./authentication/login'],{queryParams:{'redirectURL':state.url}});
          return false;
   }
  }

}
