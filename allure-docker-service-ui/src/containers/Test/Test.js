import React, { Component } from "react";

class Test extends Component {

  componentDidUpdate(){
    console.log('Test.js componentDidUpdate');
  }
  
  render() {
    console.log('RENDERING...');

    return (
      <React.Fragment>
          SARASA
      </React.Fragment>
    );
  }
}
export default Test