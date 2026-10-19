import Flutter
import UIKit
import XCTest

class RunnerTests: XCTestCase {

  func testBundleHasDisplayName() {
    let name = Bundle.main.object(forInfoDictionaryKey: "CFBundleDisplayName") as? String
    XCTAssertEqual(name, "Scam Radar")
  }

}
