FishSim3

A deterministic, extensible fish tank simulator built with Python, Pygame, and a custom ECS architecture.

This project follows strict clean-architecture boundaries and is engineered for incremental growth: additional systems, tools, UI overlays, gameplay features, and simulation loops can be added without rewriting the core engine.

🧠 Developer Guide (Codex Instructions Included)

These instructions help AI assistants (Codex/Copilot/ChatGPT) work with the project correctly and consistently.

Tone & Style Guidelines for AI Assistants

Speak in a calm, friendly, neutral tone.

Prefer small, incremental steps over major rewrites.

When modifying code:

Provide drop-in replacements or complete file snippets.

Explain what changed and why, briefly and clearly.

Assume developer (Lennart) is experienced with programming; avoid beginner explanations unless requested.

Keep messages helpful and direct, not overly enthusiastic.

Architectural Rules

FishSim3 uses a clean layered architecture:

engine/        # ECS + scheduler + events + resources (no fish/game/Pygame)
adapters/      # Pygame integration (rendering, input, audio, asset loading)
game/          # Domain logic (components, systems, factories, rules, JSON data)
app/           # Composition root (boot, main loop wiring)

Mandatory constraints:
❗ No Pygame imports anywhere inside engine/ or game/.
❗ Only systems contain logic; components contain only data.
❗ Entity creation/destruction must go through world.queue_command() and be applied by world.flush_commands().
❗ Scheduler flushes commands exactly once per frame after post_update.
ECS Expectations (for AI)

World

Stores components by type.

Provides view(ComponentA, ComponentB, ...) for iteration.

Maintains a command queue with CreateEntityCmd and DestroyEntityCmd.

System

Has a phase: pre_update, logic, post_update, or render.

Reads/writes components.

Never directly performs I/O (except adapter systems).

Scheduler

Runs systems in phase order.

Calls world.flush_commands() once per frame.

EventBus

Used for decoupled communication (input → gameplay, gameplay → audio).

Testing Expectations

Prefer deterministic systems (use rng_ai, rng_spawns, etc.).

Provide pytest snippets when adding new systems or behaviour.

Tests should be small, direct, and use World() instances isolated per test.

🐟 FishSim3 Design Document

This is the condensed design doc the project is built on.

1. Goals
Clean architecture

Reusable engine

Game logic decoupled from Pygame

Clear folder boundaries

Testability & determinism

Systems small and testable in isolation

Deterministic RNG & reproducible simulations

Performance (but simple first)

Enough efficiency for hundreds of entities

Leave room for later optimization

Easy feature development

Add new components/systems without complex plumbing

Folder structure intuitive for future contributors

2. Folder Structure (Target)
engine/
  ecs/               # world, systems, components, commands, views
  scheduling/        # scheduler + phases
  events/            # EventBus (pub/sub)
  resources/         # ResourceStore
  math/              # vector helpers (later)
  time/              # time utilities (later)
  serialization/     # save/load/replay (future)

adapters/
  pygame_render/     # Renderer, PygameApp
  pygame_input/      # input → events (ClickWorld, ClickUI)
  audio_pygame/      # sounds reacting to events
  asset_loader/      # load images, fonts, audio

game/
  components/        # pure data (Position, Fish, Hunger, SpriteRef...)
  systems/           # logic & render systems
  factories/         # build fish, eggs, pellets, tanks
  rules/             # population, growth, aging, prices
  scenes/            # TankScene, MenuScene (later)
  data/              # readable configs (species.json, tanks.json)

app/
  boot.py            # build engine, load configs, wire systems
  main.py            # entrypoint

3. Engine Concepts
ECS World

Entity ID generator

Component stores

Cached views invalidated on writes

Command queue for structural changes

System

Declares a phase

Reads/writes components, resources

Pure logic

Scheduler

Runs pre_update → logic → post_update → render

Calls world.flush_commands() once per frame

EventBus

publish(event)

subscribe(EventType, callback)

ResourceStore

Central locator for configs, RNG, renderer, assets, event bus

4. Adapters Layer
Pygame Render

Initializes window + renderer

Handles resizing

Provides draw_rect() and draw_image()

Uniform logical → screen scaling

Pygame Input

Converts raw events into domain events:

ClickWorld(x, y)

ClickUI(id)

Scroll(delta)

Audio Adapter

Listens for game events (fish died, pellet dropped)

Plays appropriate sound

Asset Loader

Loads:

images

sounds

fonts (later)

5. Game Layer
Components

Examples:

Position, Velocity, MovementIntent

Fish, Brain, Hunger, Health

RectSprite, SpriteRef

Tank, TankBounds, InTank

Pellet, Egg

Systems

FishFSMSystem → AI state machine

MovementSystem → integrate + clamp + bounce

PlacementSystem → clicks spawn pellets

HungerSystem

HealthSystem

EatPelletSystem

RectRenderSystem

SpriteRenderSystem

UI systems (future)

Factories

Only factories know how to convert data configs into component bundles:

create_fish()

create_egg()

create_pellet()

create_tank()

6. Scenes & App
Scenes

A Scene contains:

Its own World + Scheduler

Systems per phase

Initialization (factory-built entities)

App

Loads config

Creates ResourceStore

Creates first Scene

Runs PygameApp main loop

7. Roadmap Summary
Phase 1

ECS command cleanup (DONE)

Scheduler flush position (DONE)

Phase 2

Sprite system

Image loading

Replace RectSprite temporarily or overlay

Phase 3

Input adapter → domain events

PlacementSystem → Pellets/Eggs

Phase 4

Hunger → Health → Death loop

Phase 5

UI toolbar, windows, fish inspector

Tool-based interactions

Phase 6

SceneManager

Title menus / Tank selection

Phase 7

Asset polish, sound, particles

Save/load & replay (future)

✔ Development Notes for Codex/Copilot

This project expects helpers (AI coding assistants) to:

Respect the architecture boundaries.

Produce drop-in code.

Use deterministic code paths.

Avoid redesigning ECS unless requested.

Suggest tests for new systems.

Maintain readability + clean style.