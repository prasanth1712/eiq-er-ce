// import { Injectable } from '@angular/core';
// import { Router, CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot, UrlTree } from '@angular/router';
// import { Observable } from 'rxjs';

// // import { AuthenticationService } from '../_services/authentication.service';

// @Injectable({
//   providedIn: 'root'
// })
// export class AuthGuard implements CanActivate {
//   constructor(
//         private router: Router,
//         // private authentication: AuthenticationService
//     ) { }

//   canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot) {
//     // const currentUser = this.authentication.currentUserValue;
//           if (currentUser) {
//               // logged in so return true
//               return true;
//           }
//           // alert('test');
//             setTimeout(() => {
//               this.router.navigate(['./authentication/login']);
//               location.reload();
//               },100);
//           return false;
//   }

// }
