import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { AddQueryComponent } from './add-query.component';

describe('AddQueryComponent', () => {
  let component: AddQueryComponent;
  let fixture: ComponentFixture<AddQueryComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ AddQueryComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AddQueryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
