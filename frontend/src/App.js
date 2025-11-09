import { BrowserRouter, Switch, Route, Link } from "react-router-dom";
import Register from "./Register";
import Login from "./Login";

export default function App() {
  return (
    <BrowserRouter>
      <Switch>

        <Route exact path="/">
          <div className="container">
            <h1 className="title">AI Tutor</h1>
            <h2 className="quote">“Study like you're going to live forever.”</h2>

            <div className="btn-box">
              <Link to="/register"><button className="btn">Register</button></Link>
              <Link to="/login"><button className="btn">Login</button></Link>
            </div>
          </div>
        </Route>

        <Route path="/register" component={Register} />
        <Route path="/login" component={Login} />

      </Switch>
    </BrowserRouter>
  );
}
