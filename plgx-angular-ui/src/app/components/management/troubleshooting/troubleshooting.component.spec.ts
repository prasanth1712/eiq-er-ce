import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { TroubleshootingComponent } from './troubleshooting.component';

describe('TroubleshootingComponent', () => {
  let component: TroubleshootingComponent;
  let fixture: ComponentFixture<TroubleshootingComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ TroubleshootingComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TroubleshootingComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
