import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { IocComponent } from './ioc.component';

describe('IocComponent', () => {
  let component: IocComponent;
  let fixture: ComponentFixture<IocComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ IocComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(IocComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
