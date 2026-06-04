---
name: clean-code-summary
description: 'Reference clean code principles for readability, maintainability, naming, function design, tests, and code smell checks. Use when reviewing code quality, planning refactors, or checking whether a change stays simple and understandable.'
argument-hint: 'Describe the code, change, or review target you want evaluated against the clean code summary.'
---

# Clean Code Summary

Code is clean if it can be understood easily by everyone on the team. Clean code can be read and enhanced by a developer other than its original author. With understandability comes readability, changeability, extensibility, and maintainability.

## General Rules

1. Follow standard conventions.
2. Keep it simple stupid. Simpler is always better. Reduce complexity as much as possible.
3. Boy scout rule. Leave the campground cleaner than you found it.
4. Always find root cause. Always look for the root cause of a problem.

## Design Rules

1. Keep configurable data at high levels.
2. Prefer polymorphism to if/else or switch/case.
3. Separate multi-threading code.
4. Prevent over-configurability.
5. Use dependency injection.
6. Follow Law of Demeter. A class should know only its direct dependencies.

## Understandability Tips

1. Be consistent. If you do something a certain way, do all similar things in the same way.
2. Use explanatory variables.
3. Encapsulate boundary conditions. Boundary conditions are hard to keep track of. Put the processing for them in one place.
4. Prefer dedicated value objects to primitive type.
5. Avoid logical dependency. Do not write methods that work correctly depending on something else in the same class.
6. Avoid negative conditionals.

## Names Rules

1. Choose descriptive and unambiguous names.
2. Make meaningful distinction.
3. Use pronounceable names.
4. Use searchable names.
5. Replace magic numbers with named constants.
6. Avoid encodings. Do not append prefixes or type information.

## Functions Rules

1. Small.
2. Do one thing.
3. Use descriptive names.
4. Prefer fewer arguments.
5. Have no side effects.
6. Do not use flag arguments. Split methods into several independent methods that can be called from the client without the flag.

## Comments Rules

1. Always try to explain yourself in code.
2. Do not be redundant.
3. Do not add obvious noise.
4. Do not use closing brace comments.
5. Do not comment out code. Just remove it.
6. Use comments as explanation of intent.
7. Use comments as clarification of code.
8. Use comments as warning of consequences.

## Source Code Structure

1. Separate concepts vertically.
2. Related code should appear vertically dense.
3. Declare variables close to their usage.
4. Dependent functions should be close.
5. Similar functions should be close.
6. Place functions in the downward direction.
7. Keep lines short.
8. Do not use horizontal alignment.
9. Use white space to associate related things and disassociate weakly related things.
10. Do not break indentation.

## Objects and Data Structures

1. Hide internal structure.
2. Prefer data structures.
3. Avoid hybrid structures that are half object and half data.
4. Should be small.
5. Do one thing.
6. Use a small number of instance variables.
7. A base class should know nothing about its derivatives.
8. It is better to have many functions than to pass some code into a function to select a behavior.
9. Prefer non-static methods to static methods.

## Tests

1. One assert per test.
2. Readable.
3. Fast.
4. Independent.
5. Repeatable.

## Code Smells

1. Rigidity. The software is difficult to change. A small change causes a cascade of subsequent changes.
2. Fragility. The software breaks in many places due to a single change.
3. Immobility. You cannot reuse parts of the code in other projects because of involved risks and high effort.
4. Needless complexity.
5. Needless repetition.
6. Opacity. The code is hard to understand.
