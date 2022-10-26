import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { YaraComponent } from './yara.component';

describe('YaraComponent', () => {
  let component: YaraComponent;
  let fixture: ComponentFixture<YaraComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ YaraComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(YaraComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
