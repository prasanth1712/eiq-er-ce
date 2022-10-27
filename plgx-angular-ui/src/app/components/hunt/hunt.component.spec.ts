import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { HuntComponent } from './hunt.component';

describe('HuntComponent', () => {
  let component: HuntComponent;
  let fixture: ComponentFixture<HuntComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ HuntComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(HuntComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
