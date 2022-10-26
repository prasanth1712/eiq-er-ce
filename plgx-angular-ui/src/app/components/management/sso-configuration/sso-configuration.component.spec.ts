import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { SsoConfigurationComponent } from './sso-configuration.component';

describe('SsoConfigurationComponent', () => {
  let component: SsoConfigurationComponent;
  let fixture: ComponentFixture<SsoConfigurationComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ SsoConfigurationComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SsoConfigurationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
