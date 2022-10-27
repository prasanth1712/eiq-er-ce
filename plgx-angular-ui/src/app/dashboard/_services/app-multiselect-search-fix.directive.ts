import { Directive, HostListener } from '@angular/core';

@Directive({
  selector: '[promptSearch]'
})
export class MultiselectSearchFixDirective {
  // trigger an additional change detection cycle
  @HostListener('keydown') onKeydownHandler() {
    console.log('called')
    setTimeout(()=>{});
  }
}